import React, { useState, useEffect } from 'react';
import { render, Text, Box } from 'ink';
import Gradient from 'ink-gradient';
import BigText from 'ink-big-text';
import Spinner from 'ink-spinner';

const FancyTerminal: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        // Simulate loading progress
        const interval = setInterval(() => {
            setProgress((prev) => {
                if (prev < 100) {
                    return prev + 10;
                } else {
                    setLoading(false);
                    clearInterval(interval);
                    return 100;
                }
            });
        }, 500);

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
