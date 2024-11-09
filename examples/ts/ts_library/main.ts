import { formatNamePretty, NameStyle } from 'examples/ts/ts_library/formatting/formatting';

const name: string = "Juan Munoz";
const style: NameStyle = NameStyle.Fancy;

const formattedName = formatNamePretty(name, style);

console.log(`Formatted Name: ${formattedName}`);
