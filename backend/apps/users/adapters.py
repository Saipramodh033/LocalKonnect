from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Default user_type for social signups if not set, read from cookie
        if not user.user_type:
            user_type = request.COOKIES.get('expected_user_type', 'customer')
            # Validate user type
            if user_type not in ['customer', 'contractor']:
                user_type = 'customer'
            user.user_type = user_type
        return user
