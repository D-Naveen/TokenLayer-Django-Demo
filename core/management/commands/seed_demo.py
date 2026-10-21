from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile, Asset, TokenConfiguration, AuditLog

class Command(BaseCommand):
    help = 'Create demo accounts and sample TokenLayer assets.'
    def handle(self, *args, **options):
        accounts = [
            ('admin','Platform','Admin','admin','TokenLayer Platform',True),
            ('issuer','Aarav','Shah','issuer','Urban Assets Pvt Ltd',False),
            ('investor','Mira','Rao','investor','Demo Investor',False),
            ('compliance','Riya','Nair','compliance','TokenLayer Compliance',False),
            ('custodian','Dev','Menon','custodian','Demo Custody Bank',False),
        ]
        users={}
        for username,first,last,role,org,staff in accounts:
            user,created=User.objects.get_or_create(username=username,defaults={'first_name':first,'last_name':last,'email':f'{username}@tokenlayer.demo','is_staff':staff,'is_superuser':staff})
            if created: user.set_password('Demo@123')
            user.first_name=first; user.last_name=last; user.is_staff=staff; user.is_superuser=staff; user.save()
            Profile.objects.update_or_create(user=user,defaults={'role':role,'organization':org})
            users[username]=user
        examples=[
            {'name':'Urban Spaces Fund','symbol':'USF','asset_type':'Real Estate','description':'A demo fractional ownership opportunity backed by a fictional commercial property portfolio in Bengaluru. Illustrative yield and valuation are for product demonstration only.','location':'Bengaluru, Karnataka','total_value':'25000000','expected_yield':'8.40','minimum_investment':'1000','status':'Live','supply':25000,'minted':12000,'price':'1000'},
            {'name':'GreenGrid Solar Notes','symbol':'GSN','asset_type':'Infrastructure','description':'A fictional renewable infrastructure note designed to demonstrate asset onboarding, token configuration and investor allocation. No real project or security is represented.','location':'Karnataka, India','total_value':'12000000','expected_yield':'9.20','minimum_investment':'5000','status':'Live','supply':12000,'minted':8000,'price':'1000'},
            {'name':'TradeFlow Receivables','symbol':'TFR','asset_type':'Invoice / Receivables','description':'A sample invoice-backed asset for demonstrating private credit and receivables workflows in the TokenLayer sandbox.','location':'Mumbai, Maharashtra','total_value':'5000000','expected_yield':'10.00','minimum_investment':'2500','status':'Under Review','supply':5000,'minted':0,'price':'1000'},
            {'name':'Deccan Logistics Hub','symbol':'DLH','asset_type':'Real Estate','description':'A fictional logistics facility asset in the draft stage. Use it to test the issuer submission and compliance review flow.','location':'Hubballi, Karnataka','total_value':'18000000','expected_yield':'7.75','minimum_investment':'10000','status':'Draft','supply':18000,'minted':0,'price':'1000'},
        ]
        for item in examples:
            asset,created=Asset.objects.get_or_create(symbol=item['symbol'],defaults={
                'name':item['name'],'asset_type':item['asset_type'],'description':item['description'],'location':item['location'],
                'issuer':users['issuer'],'jurisdiction':'India','currency':'INR','total_value':Decimal(item['total_value']),
                'expected_yield':Decimal(item['expected_yield']),'minimum_investment':Decimal(item['minimum_investment']),
                'legal_structure':'SPV','status':item['status'],'reviewed_by':users['compliance'] if item['status']=='Live' else None,
                'review_note':'Seeded sample asset for demo purposes.' if item['status']=='Live' else ''})
            if item['status']=='Live' and not hasattr(asset,'token_config'):
                TokenConfiguration.objects.create(asset=asset,token_name=item['name']+' Token',token_symbol=item['symbol']+'T',token_type='Asset-backed Token',total_supply=item['supply'],token_price=Decimal(item['price']),minimum_purchase=1,transferable=True,contract_status='Demo deployed',contract_reference='DEMO-SEED-'+item['symbol'],minted=item['minted'])
        self.stdout.write(self.style.SUCCESS('Demo data ready. Login password for all accounts: Demo@123'))
