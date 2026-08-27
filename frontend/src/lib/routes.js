// Maps a user role to its landing/dashboard route after login/registration.
export const homeForRole = (role) => {
  switch (role) {
    case 'citizen':
      return '/citizen/dashboard';
    case 'government':
      return '/gov/dashboard';
    default:
      return '/problems';
  }
};
