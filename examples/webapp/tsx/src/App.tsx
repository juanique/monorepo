import React from 'react';
import { formatNamePretty, NameStyle } from 'examples/ts/ts_library/formatting/formatting';

function App(): JSX.Element {
    return (
        <div className="App">
            <h1>Hello Vite + React + Bazel!</h1>
            <p>Formatted Name: {formatNamePretty("Juan Munoz", NameStyle.Fancy)}</p>
            <p>Edit <code>App.tsx</code> and save to test HMR updates.</p>
        </div>
    );
}

export default App;
