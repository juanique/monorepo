import React, { useEffect, useState } from 'react';
import { render, Text } from 'ink';

const FancyTerminal: React.FC = () => {
    const [lines, setLines] = useState<string[]>([
        'Welcome to the Fancy Terminal!',
        'Initializing...',
        'Loading components...'
    ]);

    useEffect(() => {
        const newLines = [
            'System check: OK',
            'Starting services...',
            'All systems operational!'
        ];

        let index = 0;
        const interval = setInterval(() => {
            if (index < newLines.length) {
                setLines((prevLines) => [...prevLines, newLines[index]]);
                index++;
            } else {
                clearInterval(interval);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <Text>
            {lines.map((line, index) => (
                <Text key={index}>{line}\n</Text>
            ))}
            <Text>Terminal ready!</Text>
        </Text>
    );
};

render(<FancyTerminal />);
