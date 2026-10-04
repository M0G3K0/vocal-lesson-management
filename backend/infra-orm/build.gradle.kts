plugins {
    id("org.jooq.jooq-codegen-gradle")
}

dependencies {
    implementation("org.jooq:jooq")
    implementation("org.flywaydb:flyway-core")
    implementation("org.flywaydb:flyway-database-postgresql")
    jooqCodegen("org.postgresql:postgresql")
}

jooq {
    configuration {
        jdbc {
            driver = "org.postgresql.Driver"
            url = System.getenv("VLM_DB_URL") ?: "jdbc:postgresql://localhost:5432/vocal_lesson_management"
            user = System.getenv("VLM_DB_USER") ?: "vocal_lesson_management"
            password = System.getenv("VLM_DB_PASSWORD") ?: "local_development_only"
        }
        generator {
            database {
                name = "org.jooq.meta.postgres.PostgresDatabase"
                inputSchema = "application"
            }
            target {
                packageName = "com.m0g3k0.vocallessonmanagement.infra.orm.generated"
                directory = "${layout.buildDirectory.get()}/generated-src/jooq/main"
            }
        }
    }
}
