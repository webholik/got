from django.contrib.auth.decorators import user_passes_test


def verification_required(function):
    actual_decorator = user_passes_test(
        lambda u: u.is_active,
    )
    if function:
        return actual_decorator(function)
    else:
        pass
    return actual_decorator
