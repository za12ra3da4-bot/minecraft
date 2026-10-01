import { CreateGame } from './components/CreateGame';
import { GameScreen } from './components/GameScreen';
import { HowToPlay } from './components/HowToPlay';
import { JoinGame } from './components/JoinGame';
import { Lobby } from './components/Lobby';
import { MainMenu } from './components/MainMenu';
import { SettingsScreen } from './components/SettingsScreen';
import { Singleplayer } from './components/Singleplayer';
import { app } from './game/AppState';
import { useStore } from './game/store';

export function App() {
  useStore(app);
  switch (app.screen) {
    case 'game':
      return app.game ? <GameScreen game={app.game} /> : <MainMenu />;
    case 'lobby':
      return <Lobby />;
    case 'create':
      return <CreateGame />;
    case 'join':
      return <JoinGame />;
    case 'singleplayer':
      return <Singleplayer />;
    case 'howto':
      return <HowToPlay />;
    case 'settings':
      return <SettingsScreen />;
    default:
      return <MainMenu />;
  }
}
