import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { SceneCta } from "./SceneCta";
import { SceneOpener } from "./SceneOpener";
import { SceneProduct } from "./SceneProduct";

export const SaasAd: React.FC = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={52} name="Opener">
        <SceneOpener />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 8 })} />
      <TransitionSeries.Sequence durationInFrames={66} name="Product">
        <SceneProduct />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={slide({ direction: "from-bottom" })}
        timing={linearTiming({ durationInFrames: 8 })}
      />
      <TransitionSeries.Sequence durationInFrames={48} name="CTA">
        <SceneCta />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
