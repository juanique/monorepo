import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import 'examples/webapp/tictactoe/src/index.css';
import App from 'examples/webapp/tictactoe/src/App';

const root = createRoot(document.getElementById('root')!);
root.render(
    <StrictMode>
        <App />
    </StrictMode>
);
