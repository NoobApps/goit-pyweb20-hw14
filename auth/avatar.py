import cloudinary
import cloudinary.uploader
from config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET.get_secret_value(),
    secure=True
)

def upload_avatar(file, public_id: str) -> str:
    """Завантажує зображення аватара в хмарне сховище Cloudinary з обрізкою 250x250.

    Args:
        file: Файловий потік зображення для завантаження.
        public_id (str): Унікальний ідентифікатор файлу в Cloudinary (зазвичай ID користувача).

    Returns:
        str: Захищене HTTPS-посилання (secure_url) на завантажений аватар.
    """
    r = cloudinary.uploader.upload(
        file, 
        public_id=f"avatars/{public_id}", 
        overwrite=True, 
        transformation=[{"width": 250, "height": 250, "crop": "fill"}]
    )
    return r.get("secure_url")