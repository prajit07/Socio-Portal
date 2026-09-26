// Maps a user role to its landing/dashboard route after login/registration.
export const homeForRole = (role) => {
  switch (role) {
    case 'citizen':
      return '/citizen/dashboard';
    case 'government':
      return '/gov/dashboard';
    case 'university_admin':
    case 'student':
    case 'faculty':
      return '/university/dashboard';
    case 'industry':
      return '/industry/dashboard';
    case 'admin':
      return '/admin/dashboard';
    default:
      return '/problems';
  }
};
