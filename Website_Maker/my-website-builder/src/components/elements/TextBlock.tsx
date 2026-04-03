import type { BuilderElement } from "@/lib/builder-types";

export function TextBlock({ element }: { element: BuilderElement }) {
  const lines = element.content.text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const headline = lines[0] ?? "Add your headline";
  const supportingLines = lines.slice(1);

  return (
    <div
      className="site-block site-text-block flex h-full w-full flex-col justify-between p-6"
      style={{
        padding: `${element.style.padding}px`,
        borderRadius: `${element.style.borderRadius}px`,
        background: element.style.background,
        color: element.style.color,
        opacity: element.style.opacity,
        textAlign: element.style.textAlign,
      }}
    >
      {element.content.eyebrow ? (
        <p className="site-eyebrow">{element.content.eyebrow}</p>
      ) : null}
      <div className="space-y-4">
        {element.content.headingLevel === "h1" ? <h1>{headline}</h1> : null}
        {element.content.headingLevel === "h2" ? <h2>{headline}</h2> : null}
        {element.content.headingLevel === "h3" ? <h3>{headline}</h3> : null}
        {element.content.headingLevel === "p" ? <p>{headline}</p> : null}
        {supportingLines.map((line, index) => (
          <p key={`${element.id}-line-${index}`}>{line}</p>
        ))}
      </div>
    </div>
  );
}
