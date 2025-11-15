from django.db import models

# Create your models here.
class categorydb(models.Model):
    Category_name=models.CharField(max_length=100,null=True,blank=True)
    Description=models.CharField(max_length=100,null=True,blank=True)
    Image = models.ImageField(upload_to='', null=True, blank=True)

class fooditems(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(categorydb, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='', blank=True, null=True)
    availability = models.BooleanField(default=True)
