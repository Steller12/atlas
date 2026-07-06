resource "random_pet" "server" {
  length = 3
}

resource "null_resource" "app" {
  triggers = {
    server = random_pet.server.id
  }
}