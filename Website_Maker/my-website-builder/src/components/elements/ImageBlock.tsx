import type { BuilderElement } from "@/lib/builder-types";

export function ImageBlock({ element }: { element: BuilderElement }) {
  return (
    <div
      className="site-block h-full w-full"
      style={{
        borderRadius: `${element.style.borderRadius}px`,
        overflow: "hidden",
        opacity: element.style.opacity,
      }}
    >
      <div
        className="h-full w-full bg-cover bg-center"
        style={{
          backgroundImage: `linear-gradient(180deg, rgba(6, 12, 34, 0.04), rgba(6, 12, 34, 0.24)), url(${element.content.src})`,
        }}
      />
      {element.content.caption ? (
        <div className="absolute inset-x-4 bottom-4 rounded-full bg-white/22 px-4 py-2 text-sm text-white backdrop-blur-md">
          {element.content.caption}
        </div>
      ) : null}
    </div>
  );
}
