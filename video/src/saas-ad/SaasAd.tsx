import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { SceneCta } from "./SceneCta";
import { SceneHook } from "./SceneHook";
import { SceneProduct } from "./SceneProduct";

export const SaasAd: React.FC = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={44} name="Hook">
        <SceneHook />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 8 })} />
      <TransitionSeries.Sequence durationInFrames={72} name="Product">
        <SceneProduct />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={slide({ direction: "from-bottom" })}
        timing={linearTiming({ durationInFrames: 8 })}
      />
      <TransitionSeries.Sequence durationInFrames={50} name="CTA">
        <SceneCta />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
