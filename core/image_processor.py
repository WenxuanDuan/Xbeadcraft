from __future__ import annotations

from PIL import Image, ImageOps


class ImageProcessor:

    def __init__(self):
        pass

    @staticmethod
    def remove_transparent_border(
        image: Image.Image,
    ) -> Image.Image:
        """
        裁掉透明边缘
        """

        rgba = image.convert("RGBA")

        alpha = rgba.getchannel("A")

        bbox = alpha.getbbox()

        if bbox is None:
            return rgba

        return rgba.crop(bbox)

    @staticmethod
    def resize_keep_ratio(
        image: Image.Image,
        target_width: int,
        method: str = "lanczos",
    ) -> Image.Image:

        width, height = image.size

        ratio = height / width

        target_height = max(
            1,
            round(target_width * ratio),
        )

        methods = {
            "nearest": Image.Resampling.NEAREST,
            "lanczos": Image.Resampling.LANCZOS,
            "bicubic": Image.Resampling.BICUBIC,
        }

        return image.resize(
            (target_width, target_height),
            methods[method],
        )

    @staticmethod
    def resize(
        image: Image.Image,
        width: int,
        height: int,
        method: str = "lanczos",
    ) -> Image.Image:

        methods = {
            "nearest": Image.Resampling.NEAREST,
            "lanczos": Image.Resampling.LANCZOS,
            "bicubic": Image.Resampling.BICUBIC,
        }

        return image.resize(
            (width, height),
            methods[method],
        )

    def process(
        self,
        image: Image.Image,
        width: int,
        keep_ratio: bool = True,
        trim: bool = True,
        method: str = "lanczos",
    ) -> Image.Image:

        image = ImageOps.exif_transpose(image)

        image = image.convert("RGBA")

        if trim:
            image = self.remove_transparent_border(image)

        if keep_ratio:

            image = self.resize_keep_ratio(
                image,
                target_width=width,
                method=method,
            )

        return image