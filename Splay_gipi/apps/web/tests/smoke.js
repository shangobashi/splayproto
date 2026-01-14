// Minimal smoke test: file exists; real UI tests are post-MVP.
const fs = require('fs');
if (!fs.existsSync(__dirname + '/../app/page.tsx')) {
  console.error('Missing app/page.tsx');
  process.exit(1);
}
console.log('ok');
