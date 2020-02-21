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


def process_messages(request):
    """Add unread messages to Template contexts"""
    ret = {}
    if request.user.is_authenticated:
        messages = request.user.unread_messages()
        if messages:
            ret['unread_messages'] = messages

    return ret
