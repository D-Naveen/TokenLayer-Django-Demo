import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Profile, Asset, TokenConfiguration, Investment, AuditLog

def role(user):
    try: return user.profile.role
    except Profile.DoesNotExist: return 'investor'

def log_action(user, action, entity='', details=''):
    AuditLog.objects.create(user=user, action=action, entity=str(entity), details=details)

def home(request):
    if request.user.is_authenticated: return redirect('dashboard')
    return render(request, 'core/home.html')

def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username','').strip(); password = request.POST.get('password','')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user); log_action(user, 'Logged in', 'Session'); return redirect('dashboard')
        messages.error(request, 'Login details did not match. Try one of the demo accounts below.')
    return render(request, 'core/login.html')

def logout_view(request):
    if request.user.is_authenticated: log_action(request.user, 'Logged out', 'Session')
    logout(request); return redirect('login')

@login_required
def dashboard(request):
    r = role(request.user)
    if r in ('admin','compliance','custodian'):
        all_assets = Asset.objects.select_related('issuer').order_by('-created_at')
    else: all_assets = Asset.objects.filter(issuer=request.user).order_by('-created_at')
    my_assets = Asset.objects.filter(issuer=request.user)
    my_investments = Investment.objects.filter(investor=request.user, status='Completed')
    context = {'role':r,'assets':all_assets[:6], 'total_assets':my_assets.count() if r=='issuer' else Asset.objects.count(),
      'draft_count':my_assets.filter(status='Draft').count() if r=='issuer' else Asset.objects.filter(status='Draft').count(),
      'review_count':Asset.objects.filter(status='Under Review').count(), 'live_count':Asset.objects.filter(status='Live').count(),
      'token_count':TokenConfiguration.objects.aggregate(v=Sum('minted'))['v'] or 0,
      'funds_raised':my_investments.aggregate(v=Sum('amount'))['v'] or Decimal('0'),
      'investor_count':Investment.objects.filter(status='Completed').values('investor').distinct().count(),
      'recent_investments':Investment.objects.select_related('investor','asset').order_by('-created_at')[:5],
      'pending_assets':Asset.objects.filter(status='Under Review').count()}
    return render(request, 'core/dashboard.html', context)

@login_required
def assets(request):
    r=role(request.user)
    qs=Asset.objects.select_related('issuer').order_by('-created_at')
    if r=='issuer': qs=qs.filter(issuer=request.user)
    status=request.GET.get('status','')
    if status: qs=qs.filter(status=status)
    return render(request,'core/assets.html',{'assets':qs,'role':r,'selected_status':status})

@login_required
def create_asset(request):
    if role(request.user) not in ('issuer','admin'): return HttpResponseForbidden('Issuer access required for this demo action.')
    if request.method=='POST':
        try:
            value=Decimal(request.POST.get('total_value','0')); yield_value=Decimal(request.POST.get('expected_yield','0')); minimum=Decimal(request.POST.get('minimum_investment','0'))
            if value<=0 or minimum<=0 or yield_value<0: raise InvalidOperation
        except (InvalidOperation, ValueError):
            messages.error(request,'Enter valid positive financial values.'); return render(request,'core/create_asset.html',{'types':Asset.TYPES})
        asset=Asset.objects.create(name=request.POST.get('name','').strip(),symbol=request.POST.get('symbol','').strip().upper(),asset_type=request.POST.get('asset_type','Real Estate'),description=request.POST.get('description',''),location=request.POST.get('location',''),issuer=request.user,jurisdiction=request.POST.get('jurisdiction','India'),currency=request.POST.get('currency','INR'),total_value=value,expected_yield=yield_value,minimum_investment=minimum,maturity_date=request.POST.get('maturity_date') or None,legal_structure=request.POST.get('legal_structure','SPV'),document=request.FILES.get('document'),status='Draft')
        log_action(request.user,'Created asset',asset.name,f'Symbol {asset.symbol}; value {asset.currency} {asset.total_value}')
        messages.success(request,'Asset draft created. Submit it for review from the asset detail page.')
        return redirect('asset_detail',pk=asset.pk)
    return render(request,'core/create_asset.html',{'types':Asset.TYPES})

@login_required
def asset_detail(request,pk):
    asset=get_object_or_404(Asset.objects.select_related('issuer','reviewed_by'),pk=pk)
    if role(request.user)=='issuer' and asset.issuer_id!=request.user.id: return HttpResponseForbidden('You can only access your own assets.')
    investments=asset.investments.select_related('investor').order_by('-created_at')[:10]
    return render(request,'core/asset_detail.html',{'asset':asset,'role':role(request.user),'investments':investments})

@login_required
def review_asset(request,pk,decision):
    if role(request.user) not in ('admin','compliance','custodian','issuer'): return HttpResponseForbidden('Review access required.')
    asset=get_object_or_404(Asset,pk=pk)
    if role(request.user)=='issuer' and (decision!='submit' or asset.issuer_id!=request.user.id): return HttpResponseForbidden('You can only submit your own assets.')
    if request.method!='POST': return redirect('asset_detail',pk=pk)
    if decision=='submit' and role(request.user)=='issuer' and asset.issuer_id==request.user.id:
        asset.status='Under Review'; asset.save(); log_action(request.user,'Submitted asset for review',asset.name)
    elif decision in ('approve','reject'):
        if decision=='approve': asset.status='Approved'
        else: asset.status='Rejected'
        asset.reviewed_by=request.user; asset.review_note=request.POST.get('review_note','Demo review decision'); asset.save()
        log_action(request.user,f'Asset {decision}d',asset.name,asset.review_note)
        messages.success(request,f'Asset {decision}d in demo workflow.')
    elif decision=='submit':
        asset.status='Under Review'; asset.save(); log_action(request.user,'Submitted asset for review',asset.name)
    return redirect('asset_detail',pk=pk)

@login_required
def configure_token(request,pk):
    asset=get_object_or_404(Asset,pk=pk)
    if role(request.user) not in ('issuer','admin') or (role(request.user)=='issuer' and asset.issuer_id!=request.user.id): return HttpResponseForbidden('Issuer access required.')
    if asset.status not in ('Approved','Live'):
        messages.error(request,'The asset must be approved before token configuration.'); return redirect('asset_detail',pk=pk)
    config=getattr(asset,'token_config',None)
    if request.method=='POST':
        try:
            supply=int(request.POST.get('total_supply','0')); price=Decimal(request.POST.get('token_price','0')); minimum=int(request.POST.get('minimum_purchase','1')); lockup=int(request.POST.get('lockup_days','0'))
            if supply<1 or price<=0 or minimum<1 or lockup<0: raise ValueError
        except (ValueError,InvalidOperation):
            messages.error(request,'Check token supply, price, minimum purchase and lock-up.'); return render(request,'core/token_config.html',{'asset':asset,'config':config})
        defaults={'token_name':request.POST.get('token_name',asset.name+' Token'),'token_symbol':request.POST.get('token_symbol',asset.symbol+'T').upper(),'token_type':request.POST.get('token_type','Asset-backed Token'),'total_supply':supply,'token_price':price,'minimum_purchase':minimum,'transferable':request.POST.get('transferable')=='on','lockup_days':lockup}
        config,created=TokenConfiguration.objects.update_or_create(asset=asset,defaults=defaults)
        log_action(request.user,'Configured token',asset.name,f'{config.token_symbol}; supply {supply}')
        messages.success(request,'Token configuration saved. This is a local demo configuration.')
        return redirect('asset_detail',pk=pk)
    return render(request,'core/token_config.html',{'asset':asset,'config':config})

@login_required
def deploy_contract(request,pk):
    asset=get_object_or_404(Asset,pk=pk)
    if role(request.user) not in ('issuer','admin') or (role(request.user)=='issuer' and asset.issuer_id!=request.user.id): return HttpResponseForbidden('Issuer access required.')
    if request.method=='POST':
        config=getattr(asset,'token_config',None)
        if not config: messages.error(request,'Configure the token first.')
        elif asset.status not in ('Approved','Live'): messages.error(request,'Asset approval is required.')
        else:
            config.contract_status='Demo deployed'; config.contract_reference='DEMO-'+uuid.uuid4().hex[:12].upper(); config.save()
            asset.status='Live'; asset.save(update_fields=['status'])
            log_action(request.user,'Simulated smart contract deployment',asset.name,config.contract_reference)
            messages.success(request,'Demo contract deployed and asset listed in the demo marketplace. No blockchain transaction was sent.')
    return redirect('asset_detail',pk=pk)

@login_required
def mint_tokens(request,pk):
    asset=get_object_or_404(Asset,pk=pk)
    if role(request.user) not in ('issuer','admin') or (role(request.user)=='issuer' and asset.issuer_id!=request.user.id): return HttpResponseForbidden('Issuer access required.')
    if request.method=='POST':
        config=getattr(asset,'token_config',None)
        try: qty=int(request.POST.get('quantity','0'))
        except ValueError: qty=0
        if not config or config.contract_status!='Demo deployed': messages.error(request,'Deploy the demo contract before minting.')
        elif qty<1 or config.minted+qty>config.total_supply: messages.error(request,'Quantity must be positive and cannot exceed remaining supply.')
        else:
            config.minted+=qty; config.save(); log_action(request.user,'Minted demo tokens',asset.name,f'{qty} tokens; total minted {config.minted}')
            messages.success(request,f'{qty:,} demo tokens minted. This updates the local database only.')
    return redirect('asset_detail',pk=pk)

@login_required
def marketplace(request):
    qs=Asset.objects.filter(status='Live').select_related('issuer').order_by('-created_at')
    q=request.GET.get('q','').strip(); category=request.GET.get('category','')
    if q: qs=qs.filter(name__icontains=q) | qs.filter(symbol__icontains=q)
    if category: qs=qs.filter(asset_type=category)
    return render(request,'core/marketplace.html',{'assets':qs,'types':Asset.TYPES,'q':q,'category':category})

@login_required
def invest(request,pk):
    if role(request.user) not in ('investor','admin'): return HttpResponseForbidden('Investor account required.')
    asset=get_object_or_404(Asset,pk=pk,status='Live')
    config=getattr(asset,'token_config',None)
    if not config or config.contract_status!='Demo deployed': messages.error(request,'This asset is not ready for demo investment.'); return redirect('marketplace')
    if request.method=='POST':
        try: amount=Decimal(request.POST.get('amount','0'))
        except InvalidOperation: amount=Decimal('0')
        if amount < asset.minimum_investment: messages.error(request,f'Minimum investment is {asset.currency} {asset.minimum_investment:,.2f}.')
        else:
            tokens=int(amount // config.token_price)
            if tokens<config.minimum_purchase: messages.error(request,'Amount is below the token minimum purchase value.')
            elif config.minted - (asset.investments.filter(status='Completed').aggregate(v=Sum('tokens'))['v'] or 0) < tokens: messages.error(request,'Not enough minted demo tokens remain available.')
            else:
                inv=Investment.objects.create(investor=request.user,asset=asset,amount=amount,tokens=tokens,status='Completed',reference='TL-'+uuid.uuid4().hex[:10].upper())
                log_action(request.user,'Completed demo investment',asset.name,f'{amount} {asset.currency}; {tokens} tokens; ref {inv.reference}')
                messages.success(request,f'Demo investment completed. {tokens:,} tokens added to your portfolio. No real payment was taken.')
                return redirect('portfolio')
    return render(request,'core/invest.html',{'asset':asset,'config':config})

@login_required
def portfolio(request):
    investments=Investment.objects.filter(investor=request.user).select_related('asset').order_by('-created_at')
    totals=investments.filter(status='Completed').aggregate(amount=Sum('amount'),tokens=Sum('tokens'))
    return render(request,'core/portfolio.html',{'investments':investments,'total_amount':totals['amount'] or 0,'total_tokens':totals['tokens'] or 0})

@login_required
def audit(request):
    qs=AuditLog.objects.select_related('user').order_by('-created_at')
    if role(request.user) not in ('admin','compliance','custodian'): qs=qs.filter(user=request.user)
    return render(request,'core/audit.html',{'logs':qs[:150],'role':role(request.user)})
