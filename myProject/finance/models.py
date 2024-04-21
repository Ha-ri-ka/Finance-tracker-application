from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.user.username
    
class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    date = models.DateField()  # Automatically set the date when the object is created
    class Meta:
        ordering = ['-date']  # Order by date descending (newest first)
    def __str__(self):
        return f"Expense of {self.user.username} on {self.date}: {self.amount} ({self.category})"