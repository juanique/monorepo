export function prettyFormatName(name) {
    if (!name || typeof name !== 'string') {
        throw new Error("Invalid name input. Please provide a non-empty string.");
    }
    return name
        .toLowerCase()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

