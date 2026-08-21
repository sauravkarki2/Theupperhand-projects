import { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile } from "remotion";
import { ArchGallery } from "@/components/ui/arch-gallery";

/**
 * Renders the shadcn component through the `@/` alias, which is what proves
 * both the install path and the bundler alias are wired up.
 *
 * The component's own `DEFAULT_ITEMS` point at images.unsplash.com, which this
 * environment's egress policy blocks, so the deck is fed locally-generated
 * plates from `public/gallery/` instead.
 */
const ITEMS = Array.from({ length: 7 }, (_, i) => ({
  image: {
    src: staticFile(`gallery/plate-${i + 1}.png`),
    alt: `Architectural plate ${i + 1}`,
  },
}));

/**
 * Holds the render until every source has decoded.
 *
 * Remotion only knows to wait for images drawn with its own `<Img>`, which
 * wraps them in `delayRender`. `ArchGallery` is a plain DOM component using a
 * bare `<img>`, so without this the rasteriser fires while the plates are still
 * decoding and the cards come out half-painted. Preloading here keeps the
 * vendored component untouched and portable — the same trick works for any
 * third-party component that renders its own images.
 */
const usePreloadedImages = (srcs: string[]) => {
  const [handle] = useState(() => delayRender("Decoding gallery plates"));

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      srcs.map(
        (src) =>
          new Promise<void>((resolve) => {
            const img = new Image();
            img.onload = () => resolve();
            img.onerror = () => resolve();
            img.src = src;
          }),
      ),
    ).then(() => {
      if (!cancelled) {
        continueRender(handle);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [handle, srcs]);
};

export const GalleryDemo: React.FC = () => {
  usePreloadedImages(ITEMS.map((i) => i.image.src));

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#F4F4F5",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <ArchGallery items={ITEMS} cardWidth={260} cardHeight={350} cornerRadius={22} />
    </AbsoluteFill>
  );
};
