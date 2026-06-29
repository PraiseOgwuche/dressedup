export const getApiErrorMessage = (error: any, fallback: string) => {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.meta?.message ||
    error?.response?.data?.error?.code ||
    fallback
  );
};

