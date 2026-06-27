from __future__ import annotations

from dataclasses import dataclass, field

RENDER_PROFILE_0_ALLOWED = frozenset(
    {
        "static_low_poly_mesh",
        "transform",
        "unlit_color",
        "unlit_texture",
        "vertex_color",
        "alpha_blend",
        "simple_depth_test",
        "fixed_texture_count",
        "fixed_material_count",
    }
)

RENDER_PROFILE_0_FORBIDDEN = frozenset(
    {
        "dynamic_shadow",
        "arbitrary_shader",
        "particle",
        "post_processing",
        "script",
        "complex_local_physics",
    }
)


@dataclass(frozen=True)
class MeisoRenderProfile:
    profile_id: str = "meiso_render_profile_0"
    graphics_api: str = "opengl_es_2_0"
    allowed_features: frozenset[str] = field(default_factory=lambda: RENDER_PROFILE_0_ALLOWED)
    forbidden_features: frozenset[str] = field(default_factory=lambda: RENDER_PROFILE_0_FORBIDDEN)
    max_textures: int = 8
    max_materials: int = 32

    def validate_features(self, features: set[str]) -> None:
        forbidden = sorted(features & self.forbidden_features)
        if forbidden:
            raise ValueError(f"render profile rejects forbidden features: {forbidden}")
        unknown = sorted(features - self.allowed_features)
        if unknown:
            raise ValueError(f"render profile does not allow features: {unknown}")
