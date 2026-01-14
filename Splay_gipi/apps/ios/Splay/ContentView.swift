import SwiftUI
import PhotosUI

struct ContentView: View {
    @State private var selectedItem: PhotosPickerItem?
    @State private var imageData: Data?
    @State private var scan: ScanResponse?
    @State private var status: String = "idle"
    private let apiBase = ProcessInfo.processInfo.environment["API_BASE"] ?? "http://localhost:8000"

    var body: some View {
        NavigationView {
            VStack(spacing: 16) {
                Text("Splay")
                    .font(.system(size: 32, weight: .bold))

                PhotosPicker(selection: $selectedItem, matching: .images) {
                    Text("Choose Photo")
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.black)
                        .foregroundColor(.white)
                        .cornerRadius(14)
                }
                .onChange(of: selectedItem) { _, newValue in
                    Task { await loadImage(newValue) }
                }

                Button(action: { Task { await submit() } }) {
                    Text(status == "busy" ? "Scanning..." : "Scan")
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(status == "busy" ? Color.gray : Color.black)
                        .foregroundColor(.white)
                        .cornerRadius(14)
                }
                .disabled(imageData == nil || status == "busy")

                if let scan = scan {
                    Text("Status: \(scan.status)")
                        .font(.headline)
                    List {
                        ForEach(scan.items) { item in
                            Section(header: Text(item.category.replacingOccurrences(of: "_", with: " ")).textCase(.none)) {
                                ForEach(item.matches, id: \.rank) { m in
                                    Link(destination: URL(string: m.product.affiliate_url)!) {
                                        VStack(alignment: .leading, spacing: 6) {
                                            Text(m.is_budget ? "Budget pick" : "Top match")
                                                .font(.caption)
                                                .foregroundColor(m.is_budget ? .green : .primary)
                                            Text(m.product.name).font(.headline)
                                            Text(m.product.brand).font(.subheadline).foregroundColor(.secondary)
                                            Text(String(format: "$%.2f", m.product.price)).font(.title3).bold()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer()
            }
            .padding()
        }
    }

    private func loadImage(_ item: PhotosPickerItem?) async {
        guard let item else { return }
        self.scan = nil
        if let data = try? await item.loadTransferable(type: Data.self) {
            self.imageData = data
        }
    }

    private func submit() async {
        guard let imageData else { return }
        status = "busy"
        do {
            let scanId = try await createScan(imageData: imageData)
            let final = try await pollScan(scanId: scanId)
            scan = final
        } catch {
            print("Error: \(error)")
        }
        status = "idle"
    }

    private func createScan(imageData: Data) async throws -> String {
        let url = URL(string: "\(apiBase)/scans")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"room.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        req.httpBody = body

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard (resp as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
        let created = try JSONDecoder().decode(CreateScanResponse.self, from: data)
        return created.scan_id
    }

    private func pollScan(scanId: String) async throws -> ScanResponse {
        for _ in 0..<60 {
            let url = URL(string: "\(apiBase)/scans/\(scanId)")!
            let (data, _) = try await URLSession.shared.data(from: url)
            let scan = try JSONDecoder().decode(ScanResponse.self, from: data)
            if scan.status == "done" || scan.status == "failed" { return scan }
            try await Task.sleep(nanoseconds: 600_000_000)
        }
        throw URLError(.timedOut)
    }
}

struct CreateScanResponse: Decodable { let scan_id: String }

struct ScanResponse: Decodable {
    let id: String
    let status: String
    let created_at: String
    let items: [DetectedItem]
}

struct DetectedItem: Decodable, Identifiable {
    let id: String
    let category: String
    let confidence: Double
    let matches: [Match]
}

struct Match: Decodable {
    let rank: Int
    let is_budget: Bool
    let product: Product
}

struct Product: Decodable {
    let id: String
    let name: String
    let brand: String
    let category: String
    let price: Double
    let affiliate_url: String
}
