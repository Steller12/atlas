resource "random_pet" "server" {
  length = 3
}

resource "null_resource" "app" {
  triggers = {
    server_sep = random_pet.server.separator
  }
}