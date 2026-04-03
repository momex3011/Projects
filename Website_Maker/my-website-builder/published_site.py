from __future__ import annotations

import re
from typing import Any

from markupsafe import Markup, escape

DEFAULT_THEME_ID = "glassmorphism"
SURFACE_TREATMENT_BY_THEME = {
    "minimalist": "minimal",
    "brutalism": "hard",
    "neumorphism": "soft",
    "glassmorphism": "glass",
    "material": "soft",
    "cyberpunk": "neon",
    "corporate-flat": "minimal",
    "retro-90s": "hard",
    "high-contrast": "hard",
    "elegant-serif": "minimal",
}

SITE_THEME_MAP: dict[str, dict[str, str]] = {
    "minimalist": {
        "label": "Minimalist",
        "tagline": "Quiet whitespace and editorial restraint.",
        "background": "#fcfcfb",
        "surface": "rgba(255,255,255,0.9)",
        "surface_alt": "rgba(247,247,246,0.95)",
        "text": "#171717",
        "muted": "#666666",
        "accent": "#0f766e",
        "border": "rgba(23,23,23,0.08)",
        "shadow": "0 18px 40px rgba(17,24,39,0.06)",
        "radius": "24px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 12% 16%, rgba(255,255,255,0.7), transparent 20%), radial-gradient(circle at 100% 0%, rgba(15,118,110,0.08), transparent 24%)",
    },
    "brutalism": {
        "label": "Brutalism",
        "tagline": "Loud color blocks and unapologetic borders.",
        "background": "#ffef5c",
        "surface": "#fffdf6",
        "surface_alt": "#ffd8f6",
        "text": "#111111",
        "muted": "#222222",
        "accent": "#ff0054",
        "border": "#111111",
        "shadow": "10px 10px 0 #111111",
        "radius": "8px",
        "border_width": "4px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Courier New", monospace',
        "ambient": "linear-gradient(45deg, rgba(255,255,255,0.4) 0%, transparent 30%), radial-gradient(circle at 92% 10%, rgba(255,0,84,0.12), transparent 16%)",
    },
    "neumorphism": {
        "label": "Neumorphism",
        "tagline": "Soft depth with sculpted surfaces.",
        "background": "#e7ecf3",
        "surface": "#eaf0f6",
        "surface_alt": "#eef3f8",
        "text": "#304251",
        "muted": "#607386",
        "accent": "#7b5cff",
        "border": "rgba(255,255,255,0.75)",
        "shadow": "16px 16px 34px rgba(163,177,198,0.48), -16px -16px 32px rgba(255,255,255,0.9)",
        "radius": "30px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 15% 15%, rgba(255,255,255,0.72), transparent 20%), radial-gradient(circle at 85% 85%, rgba(123,92,255,0.16), transparent 20%)",
    },
    "glassmorphism": {
        "label": "Glassmorphism",
        "tagline": "Luminous layers with frosted surfaces.",
        "background": "linear-gradient(145deg, #daf1ff 0%, #f7d7ff 52%, #fff7ef 100%)",
        "surface": "rgba(255,255,255,0.28)",
        "surface_alt": "rgba(255,255,255,0.18)",
        "text": "#12243c",
        "muted": "#35506d",
        "accent": "#8e46ff",
        "border": "rgba(255,255,255,0.34)",
        "shadow": "0 24px 54px rgba(60,73,110,0.18)",
        "radius": "30px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 14% 20%, rgba(255,255,255,0.75), transparent 18%), radial-gradient(circle at 100% 0%, rgba(142,70,255,0.2), transparent 22%), radial-gradient(circle at 82% 90%, rgba(123,223,242,0.25), transparent 24%)",
    },
    "material": {
        "label": "Material Design",
        "tagline": "Balanced hierarchy with purposeful shadows.",
        "background": "#f4f7fb",
        "surface": "#ffffff",
        "surface_alt": "#eef3f9",
        "text": "#102a43",
        "muted": "#486581",
        "accent": "#2563eb",
        "border": "rgba(37,99,235,0.12)",
        "shadow": "0 18px 36px rgba(37,99,235,0.14)",
        "radius": "22px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 15% 12%, rgba(255,255,255,0.8), transparent 22%), radial-gradient(circle at 100% 0%, rgba(37,99,235,0.14), transparent 18%)",
    },
    "cyberpunk": {
        "label": "Cyberpunk",
        "tagline": "Neon glow, dark chrome, and electric edges.",
        "background": "#0d0221",
        "surface": "rgba(18, 7, 36, 0.92)",
        "surface_alt": "rgba(22, 10, 44, 0.96)",
        "text": "#f9f7ff",
        "muted": "#b9a9ff",
        "accent": "#08f7fe",
        "border": "rgba(255,0,255,0.48)",
        "shadow": "0 0 0 1px rgba(255,0,255,0.24), 0 24px 54px rgba(8,247,254,0.18)",
        "radius": "16px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Courier New", monospace',
        "ambient": "radial-gradient(circle at 12% 16%, rgba(8,247,254,0.18), transparent 16%), radial-gradient(circle at 88% 10%, rgba(255,0,255,0.2), transparent 16%), linear-gradient(180deg, rgba(255,255,255,0.02), transparent 22%)",
    },
    "corporate-flat": {
        "label": "Corporate Flat",
        "tagline": "Clean enterprise visuals with steady confidence.",
        "background": "#eef3f8",
        "surface": "#ffffff",
        "surface_alt": "#f7fafd",
        "text": "#11324d",
        "muted": "#5b7c99",
        "accent": "#0ea5e9",
        "border": "rgba(17,50,77,0.08)",
        "shadow": "0 12px 24px rgba(17,50,77,0.08)",
        "radius": "18px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 100% 0%, rgba(14,165,233,0.1), transparent 18%), radial-gradient(circle at 0% 100%, rgba(15,118,110,0.08), transparent 20%)",
    },
    "retro-90s": {
        "label": "Retro 90s",
        "tagline": "Punchy gradients and nostalgic poster energy.",
        "background": "linear-gradient(145deg, #fff2b2 0%, #ffd1dc 48%, #d2d2ff 100%)",
        "surface": "#fff9f2",
        "surface_alt": "#eaf5ff",
        "text": "#2f1443",
        "muted": "#6e4f89",
        "accent": "#ff6b6b",
        "border": "#2f1443",
        "shadow": "8px 8px 0 rgba(47,20,67,0.95)",
        "radius": "20px",
        "border_width": "3px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 12% 18%, rgba(255,255,255,0.5), transparent 18%), radial-gradient(circle at 90% 12%, rgba(255,107,107,0.18), transparent 16%), radial-gradient(circle at 82% 88%, rgba(114,9,183,0.16), transparent 16%)",
    },
    "high-contrast": {
        "label": "High-Contrast",
        "tagline": "Accessible punch with stark visual contrast.",
        "background": "#ffffff",
        "surface": "#ffffff",
        "surface_alt": "#f3f4f6",
        "text": "#000000",
        "muted": "#1f2937",
        "accent": "#ffb703",
        "border": "#000000",
        "shadow": "0 0 0 3px rgba(0,0,0,1)",
        "radius": "12px",
        "border_width": "3px",
        "border_style": "solid",
        "heading_font": '"Segoe UI", sans-serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 100% 0%, rgba(255,183,3,0.18), transparent 18%), linear-gradient(180deg, rgba(0,0,0,0.01), transparent 18%)",
    },
    "elegant-serif": {
        "label": "Elegant Serif",
        "tagline": "Quiet luxury with formal typography.",
        "background": "#f9f4ec",
        "surface": "rgba(255,249,242,0.92)",
        "surface_alt": "rgba(247,239,229,0.94)",
        "text": "#2f1d1b",
        "muted": "#6c544f",
        "accent": "#8c5e58",
        "border": "rgba(47,29,27,0.12)",
        "shadow": "0 18px 38px rgba(77,54,45,0.1)",
        "radius": "28px",
        "border_width": "1px",
        "border_style": "solid",
        "heading_font": 'Georgia, "Times New Roman", serif',
        "body_font": '"Segoe UI", sans-serif',
        "ambient": "radial-gradient(circle at 15% 12%, rgba(255,255,255,0.7), transparent 20%), radial-gradient(circle at 100% 0%, rgba(140,94,88,0.12), transparent 18%)",
    },
}


def _string_value(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or default
    return default


def _int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(value: Any, default: float = 1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _slugify(value: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "page"
    slug = base
    counter = 2

    while slug in used:
        slug = f"{base}-{counter}"
        counter += 1

    used.add(slug)
    return slug


def _inline_style(style_map: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in style_map.items():
        if value is None:
            continue
        rendered = str(value).strip()
        if not rendered:
            continue
        parts.append(f"{key}: {escape(rendered)}")
    return "; ".join(parts)


def _sort_child_ids(elements: dict[str, Any], child_ids: list[str]) -> list[str]:
    unique_ids = list(dict.fromkeys(child_ids))
    return sorted(
        unique_ids,
        key=lambda child_id: (
            _int_value(elements.get(child_id, {}).get("layout", {}).get("y"), 0),
            _int_value(elements.get(child_id, {}).get("layout", {}).get("x"), 0),
            _int_value(elements.get(child_id, {}).get("layout", {}).get("zIndex"), 0),
        ),
    )


def _content_height_for_children(
    elements: dict[str, Any],
    child_ids: list[str],
    minimum_height: int,
) -> int:
    max_child_bottom = minimum_height

    for child_id in child_ids:
        element = elements.get(child_id)
        if not isinstance(element, dict):
            continue

        layout = element.get("layout", {})
        max_child_bottom = max(
            max_child_bottom,
            _int_value(layout.get("y"), 0) + _int_value(layout.get("height"), 220),
        )

    return max(minimum_height, max_child_bottom + 84)


def _render_text_block(element: dict[str, Any]) -> str:
    content = element.get("content", {})
    style = element.get("style", {})
    lines = [
        line.strip()
        for line in _string_value(content.get("text")).splitlines()
        if line.strip()
    ]
    headline = escape(lines[0] if lines else "Add your headline")
    supporting_lines = lines[1:]
    heading_tag = _string_value(content.get("headingLevel"), "h2")
    if heading_tag not in {"h1", "h2", "h3", "p"}:
        heading_tag = "h2"

    block_style = _inline_style(
        {
            "padding": f"{max(_int_value(style.get('padding'), 24), 0)}px",
            "border-radius": f"{max(_int_value(style.get('borderRadius'), 28), 0)}px",
            "background": style.get("background"),
            "color": style.get("color"),
            "opacity": max(min(_float_value(style.get("opacity"), 1), 1), 0.1),
            "text-align": _string_value(style.get("textAlign"), "left"),
        }
    )
    eyebrow = _string_value(content.get("eyebrow"))
    eyebrow_markup = (
        f'<p class="published-eyebrow">{escape(eyebrow)}</p>' if eyebrow else ""
    )
    supporting_markup = "".join(
        f'<p class="published-copy">{escape(line)}</p>' for line in supporting_lines
    )

    return (
        f'<article class="published-block published-text-block" style="{block_style}">'
        f"{eyebrow_markup}"
        '<div class="published-text-stack">'
        f"<{heading_tag}>{headline}</{heading_tag}>"
        f"{supporting_markup}"
        "</div>"
        "</article>"
    )


def _render_image_block(element: dict[str, Any]) -> str:
    content = element.get("content", {})
    style = element.get("style", {})
    block_style = _inline_style(
        {
            "border-radius": f"{max(_int_value(style.get('borderRadius'), 28), 0)}px",
            "opacity": max(min(_float_value(style.get("opacity"), 1), 1), 0.1),
        }
    )
    src = escape(_string_value(content.get("src")))
    alt = escape(_string_value(content.get("alt"), "Website image"))
    caption = _string_value(content.get("caption"))
    caption_markup = (
        f'<div class="published-image-caption">{escape(caption)}</div>'
        if caption
        else ""
    )

    return (
        f'<article class="published-block published-image-block" style="{block_style}">'
        f'<img src="{src}" alt="{alt}" class="published-image-media" />'
        f"{caption_markup}"
        "</article>"
    )


def _enabled_actions_for_element(
    backend_actions: list[dict[str, Any]],
    element_id: str,
) -> list[dict[str, Any]]:
    return [
        action
        for action in backend_actions
        if action.get("sourceElementId") == element_id and action.get("enabled")
    ]


def _render_form_block(
    element: dict[str, Any],
    backend_actions: list[dict[str, Any]],
) -> str:
    content = element.get("content", {})
    style = element.get("style", {})
    actions = _enabled_actions_for_element(backend_actions, _string_value(element.get("id")))
    success_action = next(
        (
            action
            for action in actions
            if _string_value(action.get("actionType")) == "success-message"
        ),
        None,
    )
    default_success_message = (
        "Thanks. This temporary site preview captured your message locally."
    )
    success_message = (
        (
            _string_value(success_action.get("config", {}).get("target"))
            or _string_value(success_action.get("config", {}).get("note"))
            or default_success_message
        )
        if success_action
        else default_success_message
    )

    action_badges = "".join(
        f'<span class="published-automation-badge">{escape(_string_value(action.get("label"), "Automation"))}</span>'
        for action in actions
        if _string_value(action.get("actionType")) != "success-message"
    )
    form_fields = []
    for field in content.get("fields", []):
        if not isinstance(field, dict):
            continue
        field_type = _string_value(field.get("type"), "text")
        label = escape(_string_value(field.get("label"), "Field"))
        placeholder = escape(_string_value(field.get("placeholder")))
        required = bool(field.get("required"))
        required_attr = " required" if required else ""

        if field_type == "textarea":
            control = (
                f'<textarea name="{escape(_string_value(field.get("id"), "field"))}" '
                f'placeholder="{placeholder}"{required_attr}></textarea>'
            )
        else:
            html_type = field_type if field_type in {"text", "email", "tel"} else "text"
            control = (
                f'<input type="{escape(html_type)}" name="{escape(_string_value(field.get("id"), "field"))}" '
                f'placeholder="{placeholder}"{required_attr} />'
            )

        form_fields.append(
            '<div class="published-form-field">'
            f"<label>{label}</label>"
            f"{control}"
            "</div>"
        )

    block_style = _inline_style(
        {
            "padding": f"{max(_int_value(style.get('padding'), 24), 0)}px",
            "border-radius": f"{max(_int_value(style.get('borderRadius'), 28), 0)}px",
            "background": style.get("background"),
            "opacity": max(min(_float_value(style.get("opacity"), 1), 1), 0.1),
        }
    )
    automation_row = (
        f'<div class="published-automation-row">{action_badges}</div>'
        if action_badges
        else ""
    )

    return (
        f'<article class="published-block published-form-block" style="{block_style}">'
        '<form class="published-form-preview" data-preview-form>'
        '<p class="published-eyebrow">Connected Form</p>'
        f"<h3>{escape(_string_value(content.get('title'), 'Contact form'))}</h3>"
        f'<p class="published-copy">{escape(_string_value(content.get("intro")))}</p>'
        f'<div class="published-form-grid">{"".join(form_fields)}</div>'
        '<div class="published-form-actions">'
        f'<button type="submit" class="published-submit">{escape(_string_value(content.get("submitLabel"), "Send message"))}</button>'
        '<span class="published-preview-note">Temporary deploy preview</span>'
        "</div>"
        f'<div class="published-success-banner" data-preview-success hidden>{escape(success_message)}</div>'
        f"{automation_row}"
        "</form>"
        "</article>"
    )


def _render_container_block(
    element: dict[str, Any],
    elements: dict[str, Any],
    backend_actions: list[dict[str, Any]],
    visited: set[str],
) -> str:
    style = element.get("style", {})
    child_ids = element.get("childrenIds", [])
    child_markup = _render_children_markup(
        elements,
        child_ids if isinstance(child_ids, list) else [],
        backend_actions,
        visited,
    )
    block_style = _inline_style(
        {
            "padding": f"{max(_int_value(style.get('padding'), 24), 0)}px",
            "border-radius": f"{max(_int_value(style.get('borderRadius'), 28), 0)}px",
            "background": style.get("background"),
            "opacity": max(min(_float_value(style.get("opacity"), 1), 1), 0.1),
        }
    )
    empty_state = (
        '<div class="published-empty-state">This section is ready for nested content.</div>'
        if not child_markup
        else ""
    )

    return (
        f'<article class="published-block published-container-block" style="{block_style}">'
        '<div class="published-container-header">'
        '<div>'
        '<p class="published-eyebrow">Container</p>'
        f"<h3>{escape(_string_value(element.get('name'), 'Section'))}</h3>"
        "</div>"
        f'<span class="published-container-badge">{len(child_ids) if isinstance(child_ids, list) else 0} blocks</span>'
        "</div>"
        '<div class="published-container-body">'
        f"{child_markup}"
        f"{empty_state}"
        "</div>"
        "</article>"
    )


def _render_element_markup(
    elements: dict[str, Any],
    backend_actions: list[dict[str, Any]],
    element_id: str,
    visited: set[str],
) -> str:
    if element_id in visited:
        return ""

    element = elements.get(element_id)
    if not isinstance(element, dict):
        return ""

    next_visited = set(visited)
    next_visited.add(element_id)
    element_type = _string_value(element.get("type"), "text")
    layout = element.get("layout", {})
    node_style = _inline_style(
        {
            "left": f"{_int_value(layout.get('x'), 0)}px",
            "top": f"{_int_value(layout.get('y'), 0)}px",
            "width": f"{max(_int_value(layout.get('width'), 320), 140)}px",
            "height": f"{max(_int_value(layout.get('height'), 220), 100)}px",
            "z-index": _int_value(layout.get("zIndex"), 0),
        }
    )

    if element_type == "container":
        inner_markup = _render_container_block(
            element,
            elements,
            backend_actions,
            next_visited,
        )
    elif element_type == "image":
        inner_markup = _render_image_block(element)
    elif element_type == "form":
        inner_markup = _render_form_block(element, backend_actions)
    else:
        inner_markup = _render_text_block(element)

    return (
        f'<div class="published-node published-node--{escape(element_type)}" style="{node_style}">'
        f"{inner_markup}"
        "</div>"
    )


def _render_children_markup(
    elements: dict[str, Any],
    child_ids: list[str],
    backend_actions: list[dict[str, Any]],
    visited: set[str],
) -> Markup:
    parts: list[str] = []
    for child_id in _sort_child_ids(elements, child_ids):
        parts.append(_render_element_markup(elements, backend_actions, child_id, visited))
    return Markup("".join(parts))


def build_published_context(
    *,
    project_id: int,
    project_name: str,
    payload: dict[str, Any],
    base_url: str,
    requested_page_slug: str | None = None,
) -> dict[str, Any]:
    raw_pages = payload.get("pages")
    raw_elements = payload.get("elements")
    raw_backend_actions = payload.get("backendActions")

    if not isinstance(raw_pages, list) or not isinstance(raw_elements, dict):
        raise ValueError("This project does not contain a publishable page structure yet.")

    valid_pages: list[dict[str, Any]] = []
    for page in raw_pages:
        if not isinstance(page, dict):
            continue
        root_id = _string_value(page.get("rootId"))
        if not root_id or root_id not in raw_elements:
            continue
        valid_pages.append(page)

    if not valid_pages:
        raise ValueError("This project does not contain any publishable pages yet.")

    used_slugs: set[str] = set()
    page_links: list[dict[str, Any]] = []
    current_page_id = _string_value(payload.get("currentPageId"))
    selected_page: dict[str, Any] | None = None

    for page in valid_pages:
        slug = _slugify(_string_value(page.get("name"), "page"), used_slugs)
        page_link = {
            "id": _string_value(page.get("id")),
            "name": _string_value(page.get("name"), "Untitled Page"),
            "description": _string_value(page.get("description")),
            "rootId": _string_value(page.get("rootId")),
            "slug": slug,
            "url": f"{base_url}/{slug}",
        }
        page_links.append(page_link)

        if requested_page_slug and requested_page_slug == slug:
            selected_page = page_link

    if selected_page is None and current_page_id:
        selected_page = next(
            (page for page in page_links if page["id"] == current_page_id),
            None,
        )

    if selected_page is None:
        selected_page = page_links[0]

    theme_id = _string_value(payload.get("themeId"), DEFAULT_THEME_ID)
    theme = SITE_THEME_MAP.get(theme_id, SITE_THEME_MAP[DEFAULT_THEME_ID])
    root = raw_elements.get(selected_page["rootId"], {})
    root_layout = root.get("layout", {}) if isinstance(root, dict) else {}
    backend_actions = raw_backend_actions if isinstance(raw_backend_actions, list) else []
    child_ids = root.get("childrenIds", []) if isinstance(root, dict) else []
    stage_width = max(_int_value(root_layout.get("width"), 1160), 640)
    stage_height = max(_int_value(root_layout.get("height"), 760), 480)
    content_height = _content_height_for_children(
        raw_elements,
        child_ids if isinstance(child_ids, list) else [],
        stage_height,
    )

    return {
        "project_id": project_id,
        "project_name": project_name or "Temporary Site",
        "theme": theme,
        "theme_id": theme_id,
        "surface_treatment": SURFACE_TREATMENT_BY_THEME.get(theme_id, "minimal"),
        "page_links": [
            {
                **page,
                "is_current": page["slug"] == selected_page["slug"],
            }
            for page in page_links
        ],
        "current_page": selected_page,
        "preview_width": max(stage_width + 56, 760),
        "preview_height": stage_height + 56,
        "stage_width": stage_width,
        "stage_height": stage_height,
        "content_height": content_height,
        "page_markup": _render_children_markup(
            raw_elements,
            child_ids if isinstance(child_ids, list) else [],
            backend_actions,
            {_string_value(selected_page["rootId"])},
        ),
        "has_multiple_pages": len(page_links) > 1,
    }
