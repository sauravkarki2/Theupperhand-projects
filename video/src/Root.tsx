import "./index.css";
import { Composition, Folder } from "remotion";
import { TitleCard } from "./Composition";
import { ChatAd } from "./chat-ad/ChatAd";
import { DURATION, FPS, SIZE } from "./chat-ad/theme";
import { SaasAd } from "./saas-ad/SaasAd";
import { SceneCta } from "./saas-ad/SceneCta";
import { SceneOpener } from "./saas-ad/SceneOpener";
import { SceneProduct } from "./saas-ad/SceneProduct";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ChatAd"
        component={ChatAd}
        durationInFrames={DURATION}
        fps={FPS}
        width={SIZE}
        height={SIZE}
      />
      <Composition
        id="SaasAd"
        component={SaasAd}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
      />
      <Folder name="SaasAd-Scenes">
        <Composition id="SceneOpener" component={SceneOpener} durationInFrames={52} fps={30} width={1920} height={1080} />
        <Composition
          id="SceneProduct"
          component={SceneProduct}
          durationInFrames={66}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition id="SceneCta" component={SceneCta} durationInFrames={48} fps={30} width={1920} height={1080} />
      </Folder>
      <Composition id="TitleCard" component={TitleCard} durationInFrames={150} fps={30} width={1920} height={1080} />
    </>
  );
};
