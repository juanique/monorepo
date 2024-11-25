// Select the app container
const app = document.querySelector<HTMLDivElement>('#app');

if (app) {
    // Render initial content
    app.innerHTML = `
    <h1>Hello World</h1>
    <p>Click the button below to change the message:</p>
    <button id="changeMessage">Click Me!!!</button>
    <div id="message" style="margin-top: 1em; font-size: 1.2em; color: blue;"></div>
  `;

    // Handle button click
    const button = document.querySelector<HTMLButtonElement>('#changeMessage');
    const messageDiv = document.querySelector<HTMLDivElement>('#message');

    button?.addEventListener('click', () => {
        const messages = [
            'Hello, TypeScript!',
            'Vite is awesome!',
            'You clicked the button!',
            'Dynamic content rocks!',
        ];
        const randomMessage =
            messages[Math.floor(Math.random() * messages.length)];
        if (messageDiv) messageDiv.textContent = randomMessage;
    });
}
