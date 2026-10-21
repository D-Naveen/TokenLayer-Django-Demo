from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    ROLE_CHOICES = [('admin','Platform Admin'),('issuer','Issuer'),('investor','Investor'),('compliance','Compliance Officer'),('custodian','Custodian')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='investor')
    organization = models.CharField(max_length=180, blank=True, default='Demo Organization')
    def __str__(self): return f'{self.user.username} ({self.role})'

class Asset(models.Model):
    TYPES = [('Real Estate','Real Estate'),('Bonds','Bonds'),('Private Credit','Private Credit'),('Invoice / Receivables','Invoice / Receivables'),('Funds','Funds'),('Equity','Equity'),('Gold / Commodities','Gold / Commodities'),('Infrastructure','Infrastructure'),('Carbon Credits','Carbon Credits'),('Custom Asset','Custom Asset')]
    STATUSES = [('Draft','Draft'),('Under Review','Under Review'),('Approved','Approved'),('Rejected','Rejected'),('Live','Live')]
    name = models.CharField(max_length=160)
    symbol = models.CharField(max_length=20)
    asset_type = models.CharField(max_length=40, choices=TYPES, default='Real Estate')
    description = models.TextField()
    location = models.CharField(max_length=180, blank=True)
    issuer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    jurisdiction = models.CharField(max_length=100, default='India')
    currency = models.CharField(max_length=8, default='INR')
    total_value = models.DecimalField(max_digits=16, decimal_places=2)
    expected_yield = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    minimum_investment = models.DecimalField(max_digits=14, decimal_places=2, default=1000)
    maturity_date = models.DateField(null=True, blank=True)
    legal_structure = models.CharField(max_length=40, default='SPV')
    document = models.FileField(upload_to='asset_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='Draft')
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_assets')
    review_note = models.TextField(blank=True)
    def __str__(self): return f'{self.name} ({self.symbol})'
    @property
    def total_tokens(self): return self.token_config.total_supply if hasattr(self, 'token_config') else 0
    @property
    def minted_tokens(self): return self.token_config.minted if hasattr(self, 'token_config') else 0

class TokenConfiguration(models.Model):
    TOKEN_TYPES = [('Security Token','Security Token'),('Asset-backed Token','Asset-backed Token'),('Utility Token','Utility Token'),('Fund Token','Fund Token'),('Debt Token','Debt Token'),('Invoice Token','Invoice Token'),('Fractional Ownership Token','Fractional Ownership Token')]
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='token_config')
    token_name = models.CharField(max_length=120)
    token_symbol = models.CharField(max_length=20)
    token_type = models.CharField(max_length=40, choices=TOKEN_TYPES, default='Asset-backed Token')
    total_supply = models.PositiveBigIntegerField(default=10000)
    token_price = models.DecimalField(max_digits=14, decimal_places=2, default=1000)
    minimum_purchase = models.PositiveIntegerField(default=1)
    transferable = models.BooleanField(default=False)
    lockup_days = models.PositiveIntegerField(default=0)
    contract_status = models.CharField(max_length=20, default='Not deployed')
    contract_reference = models.CharField(max_length=100, blank=True)
    minted = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class Investment(models.Model):
    STATUSES = [('Pending','Pending'),('Completed','Completed'),('Rejected','Rejected')]
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    tokens = models.PositiveBigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUSES, default='Pending')
    reference = models.CharField(max_length=24, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=180)
    entity = models.CharField(max_length=120, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self): return f'{self.action} - {self.created_at:%Y-%m-%d %H:%M}'
