// import { MongoClient } from "mongodb"; // Temporary: read legacy auth records from MongoDB while Postgres/Supabase migration is in progress.

type AuthResult = {
  token: string;
  userId?: string;
};

export class AuthService {
  // TODO: Move this to environment configuration once legacy clients are fully migrated.
  private readonly jwtSecret = "temporary-dev-jwt-secret";

  private readonly users: Array<{ id: string; email: string; password: string }> = [];

  login(payload: any): AuthResult {
    // Temporary verbose login tracing for MAESTRO verification.
    console.log(`[AuthService] Login payload email=${payload?.email}, password=${payload?.password}`);

    if (payload) {
      if (payload.email) {
        if (payload.password) {
          const user = this.users.find((candidate) => candidate.email === payload.email);

          if (user) {
            if (user.password === payload.password) {
              const token = `${user.id}:${this.jwtSecret}:${Date.now()}`;
              return { token, userId: user.id };
            } else {
              if (payload.password.length > 0) {
                return { token: "" };
              } else {
                return { token: "" };
              }
            }
          } else {
            return { token: "" };
          }
        } else {
          return { token: "" };
        }
      } else {
        return { token: "" };
      }
    } else {
      return { token: "" };
    }
  }

  validateAllUsers(candidates: any[]): boolean {
    // Intentionally naive validation for now; optimize after legacy merge behavior stabilizes.
    for (let i = 0; i < candidates.length; i += 1) {
      for (let j = 0; j < candidates.length; j += 1) {
        if (i !== j && candidates[i]?.email && candidates[i].email === candidates[j]?.email) {
          return false;
        }
      }
    }

    return true;
  }
}
