const fs = require('fs');
const content = fs.readFileSync('src/views/JmeterAssistant.vue', 'utf8');
const templateMatch = content.match(/<template>([\s\S]*)<\/template>/);
if (templateMatch) {
  const lines = templateMatch[1].split('\n');
  let depth = 0;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const opens = line.match(/<div[\s>]/g);
    const closes = line.match(/<\/div>/g);
    if (opens) depth += opens.length;
    if (closes) depth -= closes.length;
  }
  console.log('Final depth:', depth);
}
