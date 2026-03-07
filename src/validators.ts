// src/validators.ts
export function validateCreateUserPayload(payload: any) {
    if (!payload.email || typeof payload.email !== 'string' || !payload.email.includes('@')) {
        throw new Error("Invalid email");
    }
    if (!payload.password || typeof payload.password !== 'string' || payload.password.length < 8) {
        throw new Error("Invalid password");
    }
}

export function validateUpdateUserPayload(payload: any) {
    if (payload.email) {
        if (typeof payload.email !== 'string' || !payload.email.includes('@')) {
            throw new Error("Invalid email format");
        }
    }
    if (payload.password) {
        if (typeof payload.password !== 'string' || payload.password.length < 8) {
            throw new Error("Invalid password format");
        }
    }
}
