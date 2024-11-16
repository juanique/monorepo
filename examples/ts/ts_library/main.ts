import { formatNamePretty, NameStyle } from 'examples/ts/ts_library/formatting/formatting';

const name: string = "Juan Munoz";
const formattedName = formatNamePretty(name, NameStyle.Fancy);

console.log(`Formatted Name: ${formattedName}`);
