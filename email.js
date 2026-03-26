const allowedEmailDomain =  'admin.com';

const email = 'test@admin.com';

if (email.split('@')[1] === allowedEmailDomain) {
    // do something, we accepts this email
} else {
    // return an error or do nothing 
}