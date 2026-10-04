dependencies {
    implementation(project(":domain"))
    implementation(project(":usecase"))
    implementation(project(":infra-orm"))

    implementation("org.springframework.boot:spring-boot-starter-jdbc")
}
