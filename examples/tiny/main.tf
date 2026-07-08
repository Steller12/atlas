resource "random_pet" "server" {
  length = 2
}

resource "null_resource" "app" {
  triggers = {
    server = random_pet.server.id
  }
}