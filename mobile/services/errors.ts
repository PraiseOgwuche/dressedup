/** Turn axios / API envelope errors into a user-visible string. */
export const getApiErrorMessage = (error: any, fallback: string): string => {
  const data = error?.response?.data;

  if (typeof data?.detail === 'string') {
    return data.detail;
  }

  const envelopeDetails = data?.error?.details;
  if (typeof envelopeDetails === 'string') {
    return envelopeDetails;
  }
  if (Array.isArray(envelopeDetails) && envelopeDetails.length > 0) {
    const first = envelopeDetails[0];
    if (typeof first === 'string') return first;
    if (typeof first?.msg === 'string') return first.msg;
  }

  if (typeof data?.meta?.message === 'string' && data.meta.message !== 'Validation error') {
    return data.meta.message;
  }

  if (error?.code === 'ECONNABORTED' || String(error?.message || '').toLowerCase().includes('timeout')) {
    return 'Server is waking up (this can take up to a minute on the free tier). Please try again.';
  }

  if (!error?.response) {
    return 'Cannot reach the server. Check your internet connection and try again.';
  }

  if (typeof data?.meta?.message === 'string') {
    return data.meta.message;
  }

  return fallback;
};
