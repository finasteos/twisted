// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "DecisionEngine",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "DecisionEngine",
            targets: ["DecisionEngine"]
        )
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "DecisionEngine",
            dependencies: [],
            path: "DecisionEngine"
        )
    ]
)
