import tsParser from '@typescript-eslint/parser';
export default [{ignores:['dist']},{files:['src/**/*.{ts,tsx}'],languageOptions:{parser:tsParser,parserOptions:{ecmaFeatures:{jsx:true}}},rules:{}}];
