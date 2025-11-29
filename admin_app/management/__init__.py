from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from admin_app.models import categorydb
import os

class Command(BaseCommand):
    help = 'Test Cloudinary configuration by uploading a sample image'

    def handle(self, *args, **options):
        self.stdout.write('Testing Cloudinary configuration...\n')
        
        # Check if Cloudinary env vars are set
        from django.conf import settings
        cloud_name = os.getenv('CLOUD_NAME')
        api_key = os.getenv('API_KEY')
        api_secret = os.getenv('API_SECRET')
        
        if not all([cloud_name, api_key, api_secret]):
            self.stdout.write(
                self.style.ERROR(
                    '❌ Cloudinary environment variables not configured!\n'
                    'Please set CLOUD_NAME, API_KEY, and API_SECRET in .env file'
                )
            )
            return
        
        self.stdout.write(self.style.SUCCESS(f'✓ Found CLOUD_NAME: {cloud_name}'))
        
        # Test uploading a sample image
        try:
            # Create a simple test category with image
            category, created = categorydb.objects.get_or_create(
                Category_name='Test Category',
                defaults={'Description': 'Test description'}
            )
            
            # Create a simple test image file
            test_image_content = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\x99c\xf8'
                b'\x0f\x00\x00\x01\x01\x00\x05\x00\x00\x00\x00IEND\xaeB`\x82'
            )
            
            category.Image.save('test_image.png', ContentFile(test_image_content), save=True)
            
            if category.Image:
                self.stdout.write(self.style.SUCCESS(f'✓ Image uploaded successfully!'))
                self.stdout.write(f'✓ Image URL: {category.Image.url}\n')
                self.stdout.write(self.style.SUCCESS('✅ Cloudinary is working correctly!'))
            else:
                self.stdout.write(self.style.ERROR('❌ Image URL is empty'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            traceback.print_exc()
