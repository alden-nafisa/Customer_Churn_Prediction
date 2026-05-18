const fs = require('fs');
const path = require('path');

const componentDir = 'D:\\ngoding\\Customer_Churn_Prediction\\frontend\\src\\components';

const filesToDelete = [
  'MockData.js',
  'PredictionView_New.jsx',
  'SentimentView_New.jsx'
];

filesToDelete.forEach(file => {
  const filePath = path.join(componentDir, file);
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      console.log(`✓ Deleted ${file}`);
    }
  } catch (e) {
    console.log(`✗ Could not delete ${file}: ${e.message}`);
  }
});

console.log('Cleanup complete!');
