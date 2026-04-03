import type { BuilderElement } from "@/lib/builder-types";

export function FormBlock({ element }: { element: BuilderElement }) {
  return (
    <div
      className="site-block site-form-shell h-full w-full p-6"
      style={{
        padding: `${element.style.padding}px`,
        borderRadius: `${element.style.borderRadius}px`,
        background: element.style.background,
        opacity: element.style.opacity,
      }}
    >
      <div className="space-y-3">
        <p className="site-eyebrow">Connected Form</p>
        <h3 className="text-2xl font-semibold tracking-tight text-[color:var(--site-text)]">
          {element.content.title}
        </h3>
        <p className="text-sm leading-7 text-[color:var(--site-muted)]">
          {element.content.intro}
        </p>
      </div>
      <div className="mt-6 grid gap-4">
        {element.content.fields.map((field) => (
          <div key={field.id}>
            <label>{field.label}</label>
            <div className="site-input-shell">
              {field.type === "textarea" ? `${field.placeholder} ...` : field.placeholder}
            </div>
          </div>
        ))}
      </div>
      <button className="site-submit mt-6 w-full">{element.content.submitLabel}</button>
    </div>
  );
}
