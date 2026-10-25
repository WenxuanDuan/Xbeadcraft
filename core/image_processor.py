from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageOps


class ImageProcessor:
    """Preprocess images and resize by width, height, longest side, or target bead count."""

    RESAMPLING_METHODS = {
        "nearest": Image.Resampling.NEAREST,
        "lanczos": Image.Resampling.LANCZOS,
        "bicubic": Image.Resampling.BICUBIC,
    }

    @staticmethod
    def remove_transparent_border(
        image: Image.Image,
        alpha_threshold: int = 1,
    ) -> Image.Image:
        """Crop to pixels whose alpha meets the threshold; preserve fully transparent images."""

        rgba = image.convert("RGBA")
        alpha = np.asarray(rgba.getchannel("A"))

        visible = alpha >= alpha_threshold

        if not np.any(visible):
            return rgba

        ys, xs = np.nonzero(visible)

        left = int(xs.min())
        right = int(xs.max()) + 1
        top = int(ys.min())
        bottom = int(ys.max()) + 1

        return rgba.crop((left, top, right, bottom))

    @classmethod
    def _get_resampling(
        cls,
        method: str,
    ) -> Image.Resampling:
        try:
            return cls.RESAMPLING_METHODS[method]
        except KeyError as exc:
            raise ValueError(
                f"不支持的缩放算法：{method}。"
                f"可选值：{', '.join(cls.RESAMPLING_METHODS)}"
            ) from exc

    @classmethod
    def resize_by_width(
        cls,
        image: Image.Image,
        target_width: int,
        method: str = "lanczos",
    ) -> Image.Image:
        """Resize to the target width while preserving the aspect ratio."""

        if target_width <= 0:
            raise ValueError("target_width 必须大于 0。")

        ratio = image.height / image.width

        target_height = max(
            1,
            round(target_width * ratio),
        )

        return image.resize(
            (target_width, target_height),
            cls._get_resampling(method),
        )

    @classmethod
    def resize_by_height(
        cls,
        image: Image.Image,
        target_height: int,
        method: str = "lanczos",
    ) -> Image.Image:
        """Resize to the target height while preserving the aspect ratio."""

        if target_height <= 0:
            raise ValueError("target_height 必须大于 0。")

        ratio = image.width / image.height

        target_width = max(
            1,
            round(target_height * ratio),
        )

        return image.resize(
            (target_width, target_height),
            cls._get_resampling(method),
        )

    @classmethod
    def resize_by_longest_side(
        cls,
        image: Image.Image,
        target_size: int,
        method: str = "lanczos",
    ) -> Image.Image:
        """Resize to the target longest side while preserving the aspect ratio."""

        if target_size <= 0:
            raise ValueError("target_size 必须大于 0。")

        if image.width >= image.height:
            return cls.resize_by_width(
                image,
                target_width=target_size,
                method=method,
            )

        return cls.resize_by_height(
            image,
            target_height=target_size,
            method=method,
        )

    @staticmethod
    def _visible_ratio(
        image: Image.Image,
        alpha_threshold: int,
    ) -> float:
        """Return the fraction of pixels whose alpha meets the threshold."""

        alpha = np.asarray(
            image.convert("RGBA").getchannel("A"),
            dtype=np.uint8,
        )

        if alpha.size == 0:
            return 0.0

        visible_count = int(
            np.count_nonzero(alpha >= alpha_threshold)
        )

        return visible_count / alpha.size

    @staticmethod
    def _visible_pixel_count(
        image: Image.Image,
        alpha_threshold: int,
    ) -> int:
        alpha = np.asarray(
            image.convert("RGBA").getchannel("A"),
            dtype=np.uint8,
        )

        return int(
            np.count_nonzero(alpha >= alpha_threshold)
        )

    @classmethod
    def resize_for_collection(
        cls,
        image: Image.Image,
        target_beads: int = 850,
        alpha_threshold: int = 128,
        method: str = "lanczos",
        max_side: int = 120,
    ) -> Image.Image:
        """Resize toward a target number of visible beads.

    Estimate dimensions from visible area and aspect ratio, limit the longest
    side to max_side, then refine the size using the actual visible pixel count."""

        if target_beads <= 0:
            raise ValueError("target_beads 必须大于 0。")

        rgba = image.convert("RGBA")

        if rgba.width <= 0 or rgba.height <= 0:
            raise ValueError("图片尺寸无效。")

        visible_ratio = cls._visible_ratio(
            rgba,
            alpha_threshold=alpha_threshold,
        )

        if visible_ratio <= 0:
            raise ValueError("图片中没有可见主体。")

        aspect_ratio = rgba.width / rgba.height

        # Estimate the visible bead count:
        #
        # target_width × target_height × visible_ratio
        #
        # Preserve the aspect ratio:
        #
        # target_width / target_height = aspect_ratio
        target_width = math.sqrt(
            target_beads
            * aspect_ratio
            / visible_ratio
        )

        target_height = target_width / aspect_ratio

        width = max(1, round(target_width))
        height = max(1, round(target_height))

        # Limit the output dimensions.
        longest = max(width, height)

        if longest > max_side:
            scale = max_side / longest

            width = max(1, round(width * scale))
            height = max(1, round(height * scale))

        resampling = cls._get_resampling(method)

        result = rgba.resize(
            (width, height),
            resampling,
        )

        # Resampling alpha values can change the visible bead count.
        # Refine the dimensions to approach the target bead count.
        for _ in range(5):
            actual_beads = cls._visible_pixel_count(
                result,
                alpha_threshold=alpha_threshold,
            )

            if actual_beads <= 0:
                break

            error_ratio = target_beads / actual_beads

            # Stop when the count is within approximately 3% of the target.
            if 0.97 <= error_ratio <= 1.03:
                break

            scale = math.sqrt(error_ratio)

            new_width = max(
                1,
                min(max_side, round(result.width * scale)),
            )

            new_height = max(
                1,
                min(max_side, round(result.height * scale)),
            )

            if (
                new_width == result.width
                and new_height == result.height
            ):
                break

            result = rgba.resize(
                (new_width, new_height),
                resampling,
            )

        return result

    def process(
        self,
        image: Image.Image,
        width: int = 36,
        keep_ratio: bool = True,
        trim: bool = True,
        method: str = "lanczos",
        size_mode: str = "width",
        height: int | None = None,
        target_beads: int = 850,
        alpha_threshold: int = 128,
    ) -> Image.Image:
        """Apply EXIF orientation, optional transparent-border cropping, and resizing.

    width sets the width or longest side; height sets the target height.
    collection mode uses target_beads. Disabling keep_ratio in width mode
    requires a positive height."""

        rgba = ImageOps.exif_transpose(image).convert("RGBA")

        if trim:
            rgba = self.remove_transparent_border(
                rgba,
                alpha_threshold=max(1, alpha_threshold),
            )

        if size_mode == "collection":
            return self.resize_for_collection(
                rgba,
                target_beads=target_beads,
                alpha_threshold=alpha_threshold,
                method=method,
            )

        if size_mode == "longest":
            return self.resize_by_longest_side(
                rgba,
                target_size=width,
                method=method,
            )

        if size_mode == "height":
            target_height = (
                height
                if height is not None
                else width
            )

            return self.resize_by_height(
                rgba,
                target_height=target_height,
                method=method,
            )

        if size_mode == "width":
            if keep_ratio:
                return self.resize_by_width(
                    rgba,
                    target_width=width,
                    method=method,
                )

            if height is None or height <= 0:
                raise ValueError(
                    "关闭保持比例时必须提供有效 height。"
                )

            return rgba.resize(
                (width, height),
                self._get_resampling(method),
            )

        raise ValueError(
            f"未知 size_mode：{size_mode}。"
            "可选值：width、height、longest、collection。"
        )