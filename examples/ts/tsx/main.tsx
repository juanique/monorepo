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
        <Box flexDirection="column" alignItems="center">
            <Gradient name="rainbow">
                <BigText text="Fancy Terminal" />
            </Gradient>

            <Box marginTop={1}>
                <Text color="green">Initializing...</Text>
            </Box>

            {loading ? (
                <>
                    <Box marginTop={1}>
                        <Text color="yellow">
                            <Spinner type="dots" /> Loading components...
                        </Text>
                    </Box>
                    <Box marginTop={1} width={40}>
                        <Text>
                            Progress: [{`#`.repeat(progress / 10)}{` `.repeat(10 - progress / 10)}] {progress}%
                        </Text>
                    </Box>
                </>
            ) : (
                <Box marginTop={1}>
                    <Text color="cyanBright">All systems operational! Terminal ready!</Text>
                </Box>
            )}
        </Box>
    );
};

// Render the Ink component
render(<FancyTerminal />);
