def obter_legenda_instagram(url: str):
    """Mesma lógica do notebook. Retorna (legenda, status)."""
    try:
        import instaloader

        L = instaloader.Instaloader(max_connection_attempts=1)
        if "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        elif "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        else:
            return None, "URL não reconhecida. Use um link de post (/p/) ou reel (/reel/)"

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        return post.caption, "Sucesso"
    except Exception as e:
        return None, f"Não foi possível extrair a legenda do Instagram ({type(e).__name__})"
