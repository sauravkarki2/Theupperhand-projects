import { config } from "@remotion/eslint-config-flat";

export default [
  ...(Array.isArray(config) ? config : [config]),
  {
    /**
     * Vendored shadcn/ui components are kept byte-identical to upstream so they
     * can be re-pulled or diffed against the registry. Remotion's plugin
     * legitimately objects to them — they use CSS transitions and native
     * `<img>` rather than `useCurrentFrame()` and `<Img>` — but those are
     * correct for a portable web component and are handled at the call site
     * instead (see `src/gallery/GalleryDemo.tsx`). Lint the code we author, not
     * the code we imported.
     */
    ignores: ["src/components/ui/**"],
  },
];
