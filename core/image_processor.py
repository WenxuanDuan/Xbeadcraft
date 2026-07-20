from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageOps


class ImageProcessor:
    """
    图片预处理与尺寸计算。

    支持四种尺寸模式：

    width:
        固定宽度，按比例计算高度。

    height:
        固定高度，按比例计算宽度。

    longest:
        固定最长边。

    collection:
        图鉴模式。根据主体占用面积，自动调整宽高，
        让不同造型角色的可见拼豆数量接近。
    """

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
        """
        裁掉透明边缘。

        alpha_threshold:
            Alpha 小于该值的区域视为透明。
        """

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
        """
        固定宽度并保持比例。
        """

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
        """
        固定高度并保持比例。
        """

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
        """
        固定最长边并保持比例。
        """

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
        """
        计算主体在裁剪后边界框中的占用比例。
        """

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
        """
        图鉴模式。

        目标不是统一宽度或最长边，而是让每个角色最终
        使用的可见拼豆数量接近 target_beads。

        例如：
            高瘦角色会适当放大；
            矮胖、面积较大的角色会适当缩小。

        Parameters
        ----------
        target_beads
            希望主体使用的拼豆数量。

        alpha_threshold
            Alpha 大于等于该值的像素视为需要拼豆。

        max_side
            防止极端图片生成过大的尺寸。
        """

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

        # 可见拼豆数约为：
        #
        # target_width × target_height × visible_ratio
        #
        # 同时保持：
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

        # 防止图片过大。
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

        # 缩放后 Alpha 抗锯齿会影响实际拼豆数量。
        # 通过少量迭代，让结果更接近目标值。
        for _ in range(5):
            actual_beads = cls._visible_pixel_count(
                result,
                alpha_threshold=alpha_threshold,
            )

            if actual_beads <= 0:
                break

            error_ratio = target_beads / actual_beads

            # 误差小于 3% 时，不再调整。
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
        """
        统一图片处理入口。

        Parameters
        ----------
        width
            width 模式下表示宽度；
            longest 模式下表示最长边。

        height
            height 模式下的目标高度；
            关闭保持比例时的强制高度。

        size_mode
            width / height / longest / collection

        target_beads
            collection 模式下的目标可见拼豆数量。
        """

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