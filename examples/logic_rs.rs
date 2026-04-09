fn main() {
    println!("Démarrage du module Rust...");
    match safe_calculation(10, 5) {
        Some(val) => println!("Résultat: {}", val),
        None => println!("Erreur de calcul"),
    }
}

fn safe_calculation(a: i32, b: i32) -> Option<i32> {
    if b == 0 {
        None
    } else {
        // Bloc complexe virtuel pour tester radiance
        let mut result = 0;
        for i in 0..a {
            for _j in 0..b {
                result += 1;
                if result > 100 {
                    break;
                }
            }
        }
        Some(result)
    }
}
