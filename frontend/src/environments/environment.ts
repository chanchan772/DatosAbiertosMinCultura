// Desarrollo local: usa el backend FastAPI en vivo (que ya tiene la llave DeepSeek).
export const environment = {
  staticMode: false,
  apiBase: 'http://127.0.0.1:8000',
  // No se usa en dev (las llamadas IA pasan por el backend):
  deepseekApiKey: '',
  deepseekUrl: 'https://api.deepseek.com',
  deepseekModel: 'deepseek-chat',
};
