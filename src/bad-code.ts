// src/billing.ts
export function processUserCheckout(user: any, cart: any[], paymentMethod: string, discountCode?: string) {
    let total = 0;
    for (let i = 0; i < cart.length; i++) {
        if (cart[i].type === 'physical') {
            total += cart[i].price + 5.99; // shipping
        } else {
            total += cart[i].price;
        }
    }
    
    if (discountCode) {
        if (discountCode === 'SUMMER20') total = total * 0.8;
        else if (discountCode === 'WELCOME10') total = total * 0.9;
    }
    if (paymentMethod === 'credit_card') {
        console.log(`Charging CC: ${total}`);
        if (user.isPremium) {
            console.log('Sending premium thank you email');
        } else {
            console.log('Sending standard receipt');
        }
    } else if (paymentMethod === 'paypal') {
        console.log(`Redirecting to PayPal for: ${total}`);
    }
    return true;
}
